export type PointerEventType = 'down' | 'move' | 'up' | 'cancel'

export type StrokePoint = {
  x: number
  y: number
  tMs: number
  type: PointerEventType
  pressure?: number
  tiltX?: number
  tiltY?: number
  azimuth?: number
}

export type CanvasMeta = {
  widthPx: number
  heightPx: number
  dpr: number
}

export type SamplingConfig = {
  mode: 'time' | 'distance' | 'hybrid' | 'raw'
  minIntervalMs?: number
  minDistancePx?: number
  maxPoints?: number
}

export type SmoothingConfig = {
  enabled: boolean
  kind?: 'none' | 'ema' | 'simple'
  alpha?: number
}

export type ValidationConfig = {
  minPoints: number
  minDurationMs: number
  maxDurationMs?: number
  requireClosed: boolean
  closedThresholdPx: number
  minPathLengthPx?: number
}

export type CircleFitResult = {
  centerX: number
  centerY: number
  radius: number
  rmse: number
  circularity: number
}

export type StrokeMetrics = {
  durationMs: number
  points: number
  pathLengthPx: number
  avgSpeedPxPerS: number
  maxSpeedPxPerS?: number
  closedDistancePx?: number
  fit?: CircleFitResult
}

export type StrokePayload = {
  meta: CanvasMeta
  points: StrokePoint[]
  metrics: StrokeMetrics
  previewPngBase64?: string
}

export type ValidationIssue =
  | { code: 'TOO_FEW_POINTS'; detail?: string }
  | { code: 'TOO_SHORT'; detail?: string }
  | { code: 'TOO_LONG'; detail?: string }
  | { code: 'NOT_CLOSED'; detail?: string }
  | { code: 'PATH_TOO_SHORT'; detail?: string }

export type ValidationResult = {
  ok: boolean
  issues: ValidationIssue[]
  metrics?: StrokeMetrics
}

export type CircleCanvasState = 'idle' | 'drawing' | 'completed' | 'invalid' | 'disabled'

export type ExportFormat = 'raw_points' | 'packed_deltas'

export type ExportOptions = {
  format: ExportFormat
  includePreview?: boolean
  normalize?: 'none' | '0_1'
  packedUnits?: 'px_scaled_10' | 'norm_10000'
}

export type CircleCanvasProps = {
  width: number
  height: number
  dpr?: number
  disabled?: boolean
  readOnly?: boolean
  capturePointer?: boolean
  sampling?: Partial<SamplingConfig>
  smoothing?: Partial<SmoothingConfig>
  validation?: Partial<ValidationConfig>
  showGuide?: boolean
  guideRadiusPx?: number
  showLivePath?: boolean
  showDebug?: boolean
  initialStroke?: StrokePoint[]
  maxStrokeMs?: number
  maxPoints?: number
}

export type CircleCanvasEmits = {
  (e: 'stroke:start', payload: { meta: CanvasMeta }): void
  (e: 'stroke:point', payload: { point: StrokePoint; count: number }): void
  (e: 'stroke:end', payload: { payload: StrokePayload }): void
  (e: 'stroke:validated', payload: ValidationResult): void
  (e: 'cleared'): void
  (e: 'error', payload: { code: string; message?: string }): void
  (e: 'state', payload: { state: CircleCanvasState }): void
}

export type CircleCanvasExposed = {
  getState(): CircleCanvasState
  isDirty(): boolean
  canSubmit(): boolean
  clear(): void
  undoLastPoint?(): void
  cancelStroke(): void
  getStroke(): StrokePoint[]
  getMetrics(): StrokeMetrics | null
  validate(): ValidationResult
  exportPayload(opts?: Partial<ExportOptions>): StrokePayload
  capturePreviewPngBase64(opts?: { scale?: number; quality?: number }): string
  setStroke(points: StrokePoint[], opts?: { fitToCanvas?: boolean }): void
}
