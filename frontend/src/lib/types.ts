export interface DetectionResult {
  src_ip: string;
  dst_ip: string;
  src_port: number;
  dst_port: number;
  protocol: string;
  prediction: string;
  confidence: number;
  is_unknown: boolean;
}

export interface SystemStats {
  total_detections: number;
  total_alerts: number;
  accuracy: number;
  detection_rate: number;
  attack_distribution: Record<string, number>;
}

export interface AlertItem {
  id: string;
  created_at: string;
  src_ip: string;
  dst_ip: string;
  protocol: string;
  prediction: string;
  confidence: number;
  is_unknown: boolean;
  is_attack: boolean;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error: string | null;
  meta?: { page: number; limit: number; total: number };
}
