"""
Validación automática con reconocimiento de patrones de nombres y logging detallado.
Formato esperado: [nombre]_[colorspace]_scale[número].jpg
Ejemplo: 13-_ybk_scale15.jpg
"""

import numpy as np
import cv2
from pathlib import Path
from dstretch import DecorrelationStretch
import matplotlib.pyplot as plt
import json
import re
import logging
import datetime
from collections import defaultdict

def setup_logging():
    """Configura sistema de logging detallado."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"dstretch_validation_{timestamp}.log"
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("="*80)
    logger.info("DSTRETCH PYTHON VALIDATION LOG STARTED")
    logger.info("="*80)
    
    return logger, log_filename

def calculate_simple_ssim(img1, img2):
    """Calcula SSIM simplificado usando solo NumPy."""
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    
    mu1 = np.mean(img1)
    mu2 = np.mean(img2)
    
    sigma1_sq = np.var(img1)
    sigma2_sq = np.var(img2)
    sigma12 = np.mean((img1 - mu1) * (img2 - mu2))
    
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    
    numerator = (2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)
    denominator = (mu1**2 + mu2**2 + C1) * (sigma1_sq + sigma2_sq + C2)
    
    return numerator / denominator

class SmartValidator:
    """Validador que reconoce automáticamente patrones de nombres con logging."""
    
    def __init__(self):
        self.dstretch = DecorrelationStretch()
        self.results = []
        self.logger, self.log_filename = setup_logging()
        
        # Mapeo de nombres de colorspace
        self.colorspace_mapping = {
            'yds': 'YDS', 'crgb': 'CRGB', 'lre': 'LRE', 'lds': 'LDS',
            'lab': 'LAB', 'rgb': 'RGB', 'ybr': 'YBR', 'ybk': 'YBK',
            'yre': 'YRE', 'yrd': 'YRD', 'yye': 'YYE', 'ywe': 'YWE',
            'yxx': 'YXX', 'lrd': 'LRD', 'lbk': 'LBK', 'lbl': 'LBL',
            'lwe': 'LWE', 'lye': 'LYE', 'lxx': 'LXX'
        }
        
        self.logger.info(f"Validator initialized with {len(self.colorspace_mapping)} colorspace mappings")
    
    def parse_filename(self, filename):
        """Parsea el nombre del archivo para extraer información."""
        pattern = r'^(.+?)_([a-zA-Z]+)_scale(\d+)\.jpg$'
        match = re.match(pattern, filename)
        
        if match:
            original_name = match.group(1)
            colorspace_raw = match.group(2).lower()
            scale = int(match.group(3))
            colorspace = self.colorspace_mapping.get(colorspace_raw, colorspace_raw.upper())
            
            self.logger.debug(f"Parsed {filename}: {original_name} | {colorspace} | {scale}")
            
            return {
                'original_name': original_name,
                'colorspace': colorspace,
                'scale': scale,
                'valid': True
            }
        
        self.logger.debug(f"Could not parse filename: {filename}")
        return {'valid': False}
    
    def find_original_image(self, original_name, directory="validation_images"):
        """Busca la imagen original basada en el nombre base."""
        directory = Path(directory)
        extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
        variations = [original_name, original_name.rstrip('-'), original_name.rstrip('_')]
        
        for ext in extensions:
            for variation in variations:
                for file_path in directory.rglob(f"{variation}{ext}"):
                    if file_path.exists():
                        self.logger.info(f"Original found: {variation}{ext} for {original_name}")
                        return str(file_path)
        
        self.logger.warning(f"Original image not found for: {original_name}")
        return None
    
    def discover_images(self, directory="validation_images"):
        """Descubre automáticamente todas las imágenes procesadas."""
        directory = Path(directory)
        processed_files = []
        image_groups = defaultdict(list)
        
        self.logger.info(f"Discovering images in: {directory}")
        
        for file_path in directory.rglob("*.jpg"):
            parsed = self.parse_filename(file_path.name)
            if parsed['valid']:
                processed_files.append({
                    'file_path': str(file_path),
                    'filename': file_path.name,
                    **parsed
                })
                image_groups[parsed['original_name']].append(parsed)
        
        self.logger.info(f"Discovery complete: {len(processed_files)} processed images found")
        self.logger.info(f"Grouped into {len(image_groups)} original images")
        
        for original_name, group in image_groups.items():
            colorspaces = [item['colorspace'] for item in group]
            self.logger.info(f"  {original_name}: {len(group)} variants - {colorspaces}")
        
        return processed_files, image_groups
    
    def validate_all_discovered(self, directory="."):
        """Valida todas las imágenes descubiertas automáticamente."""
        
        self.logger.info("Starting automatic validation process")
        
        processed_files, image_groups = self.discover_images(directory)
        
        if not processed_files:
            self.logger.error("No processed images found with expected pattern")
            self.logger.info("Expected pattern: [name]_[colorspace]_scale[number].jpg")
            return
        
        validated_count = 0
        failed_count = 0
        
        for file_info in processed_files:
            original_name = file_info['original_name']
            colorspace = file_info['colorspace']
            scale = file_info['scale']
            processed_path = file_info['file_path']
            
            self.logger.info(f"Processing: {file_info['filename']}")
            
            # Buscar imagen original
            original_path = self.find_original_image(original_name, directory)
            if not original_path:
                self.logger.error(f"Original image not found for: {original_name}")
                failed_count += 1
                continue
            
            # Validar esta combinación
            result = self.validate_single_image(
                original_path, processed_path, colorspace, scale, original_name
            )
            
            if result:
                validated_count += 1
                self.logger.info(f"Validation successful: {colorspace} | MSE={result['mse']:.1f} | SSIM={result['ssim']:.3f} | {result['status']}")
            else:
                failed_count += 1
                self.logger.error(f"Validation failed for: {file_info['filename']}")
        
        self.logger.info("="*50)
        self.logger.info("VALIDATION COMPLETED")
        self.logger.info(f"Successfully validated: {validated_count}")
        self.logger.info(f"Failed validations: {failed_count}")
        self.logger.info(f"Total processed: {len(processed_files)}")
        
        self.generate_comprehensive_report()
        self.export_analysis_logs()
    
    def validate_single_image(self, original_path, imagej_path, colorspace, scale, image_name):
        """Valida una imagen individual con logging detallado."""
        try:
            self.logger.debug(f"Loading images: {Path(original_path).name} | {Path(imagej_path).name}")
            
            # Cargar imágenes
            original = cv2.imread(original_path)
            original_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
            
            imagej_result = cv2.imread(imagej_path)
            imagej_rgb = cv2.cvtColor(imagej_result, cv2.COLOR_BGR2RGB)
            
            self.logger.debug(f"Image shapes - Original: {original_rgb.shape} | ImageJ: {imagej_rgb.shape}")
            
            # Procesar con nuestra implementación
            self.logger.debug(f"Processing with DStretch Python: {colorspace} scale {scale}")
            result = self.dstretch.process(original_rgb, colorspace, scale)
            our_result = result.processed_image
            
            self.logger.debug(f"Python result shape: {our_result.shape}")
            
            # Ajustar dimensiones si es necesario
            if imagej_rgb.shape != our_result.shape:
                self.logger.warning(f"Shape mismatch - ImageJ: {imagej_rgb.shape} vs Python: {our_result.shape}")
                min_h = min(imagej_rgb.shape[0], our_result.shape[0])
                min_w = min(imagej_rgb.shape[1], our_result.shape[1])
                imagej_rgb = imagej_rgb[:min_h, :min_w]
                our_result = our_result[:min_h, :min_w]
                self.logger.info(f"Images resized to: {our_result.shape}")
            
            # Calcular métricas
            mse = np.mean((imagej_rgb.astype(float) - our_result.astype(float)) ** 2)
            
            ssim_scores = []
            for c in range(3):
                ssim_c = calculate_simple_ssim(imagej_rgb[:,:,c], our_result[:,:,c])
                ssim_scores.append(ssim_c)
            ssim_avg = np.mean(ssim_scores)
            
            abs_diff = np.abs(imagej_rgb.astype(float) - our_result.astype(float))
            max_diff = np.max(abs_diff)
            mean_diff = np.mean(abs_diff)
            significant_diff_pct = np.sum(abs_diff > 10) / abs_diff.size * 100
            
            # Determinar estado
            if mse < 25 and ssim_avg > 0.95:
                status = "EXCELLENT"
            elif mse < 100 and ssim_avg > 0.90:
                status = "GOOD"
            elif mse < 300 and ssim_avg > 0.80:
                status = "ACCEPTABLE"
            else:
                status = "NEEDS_ADJUSTMENT"
            
            # Log de métricas detalladas
            self.logger.info(f"METRICS | {image_name} | {colorspace} | Scale {scale}")
            self.logger.info(f"  MSE: {mse:.2f}")
            self.logger.info(f"  SSIM: {ssim_avg:.4f} (R:{ssim_scores[0]:.3f} G:{ssim_scores[1]:.3f} B:{ssim_scores[2]:.3f})")
            self.logger.info(f"  Max Diff: {max_diff:.1f}")
            self.logger.info(f"  Mean Diff: {mean_diff:.2f}")
            self.logger.info(f"  Significant Diff: {significant_diff_pct:.1f}%")
            self.logger.info(f"  STATUS: {status}")
            
            result_data = {
                'image_name': image_name,
                'colorspace': colorspace,
                'scale': scale,
                'mse': mse,
                'ssim': ssim_avg,
                'ssim_per_channel': ssim_scores,
                'max_difference': max_diff,
                'mean_difference': mean_diff,
                'significant_diff_pct': significant_diff_pct,
                'status': status,
                'original_file': Path(original_path).name,
                'imagej_file': Path(imagej_path).name,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            # Guardar resultado
            dest_dir = Path(original_path).parent
            our_filename = dest_dir / f"python_{image_name}_{colorspace}_s{scale}.jpg"
            our_bgr = cv2.cvtColor(our_result, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(our_filename), our_bgr)
            result_data['python_file'] = str(our_filename)
            
            self.logger.debug(f"Python result saved: {our_filename}")
            
            # Crear visualización
            self.create_detailed_comparison(
                original_rgb, imagej_rgb, our_result, result_data, dest_dir=dest_dir
            )
            
            self.results.append(result_data)
            return result_data
        
        except Exception as e:
            self.logger.error(f"Validation error for {image_name} {colorspace}: {str(e)}")
            return None
    
    def create_detailed_comparison(self, original, imagej_result, our_result, metrics, dest_dir=None):
        """Crea comparación visual detallada."""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # Fila superior: imágenes
        axes[0,0].imshow(original)
        axes[0,0].set_title(f'Original\n{metrics["image_name"]}', fontsize=12, fontweight='bold')
        axes[0,0].axis('off')
        
        axes[0,1].imshow(imagej_result)
        axes[0,1].set_title(f'ImageJ DStretch\n{metrics["colorspace"]} (scale {metrics["scale"]})', 
                           fontsize=12, fontweight='bold')
        axes[0,1].axis('off')
        
        axes[0,2].imshow(our_result)
        axes[0,2].set_title(f'DStretch Python\n{metrics["colorspace"]} (scale {metrics["scale"]})', 
                           fontsize=12, fontweight='bold')
        axes[0,2].axis('off')
        
        # Fila inferior: análisis
        diff_image = np.abs(imagej_result.astype(float) - our_result.astype(float))
        
        diff_normalized = diff_image / np.max(diff_image) if np.max(diff_image) > 0 else diff_image
        axes[1,0].imshow(diff_normalized, cmap='hot')
        axes[1,0].set_title('Difference Map\n(Normalized)', fontsize=12)
        axes[1,0].axis('off')
        
        axes[1,1].hist(diff_image.flatten(), bins=50, alpha=0.7, color='red', edgecolor='black')
        axes[1,1].set_title('Difference Distribution', fontsize=12)
        axes[1,1].set_xlabel('Pixel Difference')
        axes[1,1].set_ylabel('Frequency')
        axes[1,1].grid(True, alpha=0.3)
        
        status_colors = {
            'EXCELLENT': 'darkgreen', 'GOOD': 'blue',
            'ACCEPTABLE': 'orange', 'NEEDS_ADJUSTMENT': 'red'
        }
        
        metrics_text = f"""VALIDATION METRICS

MSE: {metrics['mse']:.2f}
SSIM (avg): {metrics['ssim']:.4f}
SSIM (R): {metrics['ssim_per_channel'][0]:.4f}
SSIM (G): {metrics['ssim_per_channel'][1]:.4f}
SSIM (B): {metrics['ssim_per_channel'][2]:.4f}

Max Diff: {metrics['max_difference']:.1f}
Mean Diff: {metrics['mean_difference']:.1f}
Significant Diff: {metrics['significant_diff_pct']:.1f}%

STATUS: {metrics['status']}

Files:
Original: {metrics['original_file']}
ImageJ: {metrics['imagej_file']}
Python: {Path(metrics['python_file']).name}"""
        
        axes[1,2].text(0.05, 0.95, metrics_text, fontsize=10, 
                      verticalalignment='top', horizontalalignment='left',
                      color=status_colors.get(metrics['status'], 'black'),
                      family='monospace')
        axes[1,2].axis('off')
        
        plt.suptitle(f"Validation Report: {metrics['image_name']} - {metrics['colorspace']}", 
                     fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if dest_dir is None:
            dest_dir = Path('.')
        comparison_filename = dest_dir / f"comparison_{metrics['image_name']}_{metrics['colorspace']}_s{metrics['scale']}.png"
        plt.savefig(str(comparison_filename), dpi=150, bbox_inches='tight')
        plt.close()
        
        self.logger.debug(f"Comparison saved: {comparison_filename}")
    
    def export_analysis_logs(self):
        """Exporta logs de análisis en múltiples formatos para evaluación."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. CSV para análisis de datos
        csv_filename = f"validation_analysis_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            if self.results:
                headers = [
                    'timestamp', 'image_name', 'colorspace', 'scale',
                    'mse', 'ssim_avg', 'ssim_r', 'ssim_g', 'ssim_b',
                    'max_diff', 'mean_diff', 'significant_diff_pct', 'status',
                    'original_file', 'imagej_file', 'python_file'
                ]
                f.write(','.join(headers) + '\n')
                
                for result in self.results:
                    row = [
                        result['timestamp'], result['image_name'], result['colorspace'], str(result['scale']),
                        f"{result['mse']:.2f}", f"{result['ssim']:.4f}",
                        f"{result['ssim_per_channel'][0]:.4f}",
                        f"{result['ssim_per_channel'][1]:.4f}",
                        f"{result['ssim_per_channel'][2]:.4f}",
                        f"{result['max_difference']:.1f}", f"{result['mean_difference']:.2f}",
                        f"{result['significant_diff_pct']:.1f}", result['status'],
                        result['original_file'], result['imagej_file'],
                        Path(result['python_file']).name
                    ]
                    f.write(','.join(row) + '\n')
        
        # 2. Matriz de comparación por colorspace
        matrix_filename = f"colorspace_matrix_{timestamp}.txt"
        with open(matrix_filename, 'w', encoding='utf-8') as f:
            f.write("DSTRETCH VALIDATION MATRIX\n")
            f.write("=" * 50 + "\n\n")
            
            # Agrupar por colorspace
            cs_results = defaultdict(list)
            for result in self.results:
                cs_results[result['colorspace']].append(result)
            
            f.write("COLORSPACE PERFORMANCE SUMMARY:\n")
            f.write("-" * 50 + "\n")
            
            for cs in sorted(cs_results.keys()):
                results = cs_results[cs]
                avg_mse = np.mean([r['mse'] for r in results])
                avg_ssim = np.mean([r['ssim'] for r in results])
                excellent_count = sum(1 for r in results if r['status'] == 'EXCELLENT')
                
                f.write(f"{cs:>6}: {len(results):2d} tests | ")
                f.write(f"MSE {avg_mse:6.1f} | SSIM {avg_ssim:.3f} | ")
                f.write(f"Excellent {excellent_count:2d}/{len(results):2d}\n")
        
        # 3. Reporte de problemas específicos
        issues_filename = f"validation_issues_{timestamp}.txt"
        with open(issues_filename, 'w', encoding='utf-8') as f:
            f.write("DSTRETCH VALIDATION ISSUES REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            needs_adjustment = [r for r in self.results if r['status'] == 'NEEDS_ADJUSTMENT']
            
            if needs_adjustment:
                f.write("COLORSPACES REQUIRING ADJUSTMENT:\n")
                f.write("-" * 30 + "\n")
                
                for result in needs_adjustment:
                    f.write(f"Image: {result['image_name']}\n")
                    f.write(f"Colorspace: {result['colorspace']} (scale {result['scale']})\n")
                    f.write(f"Issues: MSE={result['mse']:.1f}, SSIM={result['ssim']:.3f}\n")
                    f.write(f"Significant differences: {result['significant_diff_pct']:.1f}%\n")
                    f.write("-" * 30 + "\n")
            else:
                f.write("No major issues found - all colorspaces performing adequately.\n")
        
        self.logger.info("Analysis logs exported:")
        self.logger.info(f"  CSV data: {csv_filename}")
        self.logger.info(f"  Matrix summary: {matrix_filename}")
        self.logger.info(f"  Issues report: {issues_filename}")
        self.logger.info(f"  Main log: {self.log_filename}")
    
    def generate_comprehensive_report(self):
        """Genera reporte completo con estadísticas detalladas."""
        
        if not self.results:
            self.logger.warning("No results available for comprehensive report")
            return
        
        self.logger.info("=" * 80)
        self.logger.info("COMPREHENSIVE VALIDATION REPORT")
        self.logger.info("=" * 80)
        
        # Estadísticas por colorspace
        colorspace_stats = defaultdict(lambda: {
            'count': 0, 'excellent': 0, 'good': 0, 'acceptable': 0, 'needs_fix': 0,
            'mse_sum': 0, 'ssim_sum': 0
        })
        
        for result in self.results:
            cs = result['colorspace']
            status = result['status'].lower()
            
            # Mapear correctamente los estados
            if status == 'needs_adjustment':
                status_key = 'needs_fix'
            elif status == 'excellent':
                status_key = 'excellent'
            elif status == 'good':
                status_key = 'good'
            elif status == 'acceptable':
                status_key = 'acceptable'
            else:
                status_key = 'needs_fix'  # fallback
            
            colorspace_stats[cs]['count'] += 1
            colorspace_stats[cs][status_key] += 1
            colorspace_stats[cs]['mse_sum'] += result['mse']
            colorspace_stats[cs]['ssim_sum'] += result['ssim']
        
        # Log del reporte por colorspace
        self.logger.info("RESULTS BY COLORSPACE:")
        self.logger.info("-" * 80)
        header = f"{'Colorspace':<10} {'Tests':<6} {'Excellent':<10} {'Good':<6} {'Accept':<7} {'Needs Fix':<10} {'Avg MSE':<8} {'Avg SSIM':<9}"
        self.logger.info(header)
        self.logger.info("-" * 80)
        
        for cs in sorted(colorspace_stats.keys()):
            stats = colorspace_stats[cs]
            avg_mse = stats['mse_sum'] / stats['count']
            avg_ssim = stats['ssim_sum'] / stats['count']
            
            line = f"{cs:<10} {stats['count']:<6} {stats['excellent']:<10} {stats['good']:<6} {stats['acceptable']:<7} {stats['needs_fix']:<10} {avg_mse:<8.1f} {avg_ssim:<9.3f}"
            self.logger.info(line)
        
        # Resumen general
        total = len(self.results)
        excellent = sum(1 for r in self.results if r['status'] == 'EXCELLENT')
        good = sum(1 for r in self.results if r['status'] == 'GOOD')
        acceptable = sum(1 for r in self.results if r['status'] == 'ACCEPTABLE')
        needs_fix = sum(1 for r in self.results if r['status'] == 'NEEDS_ADJUSTMENT')
        success_rate = (excellent + good) / total * 100 if total > 0 else 0
        
        self.logger.info("=" * 80)
        self.logger.info("FINAL SUMMARY:")
        self.logger.info(f"  Total validations: {total}")
        self.logger.info(f"  Excellent (MSE<25, SSIM>0.95): {excellent} ({excellent/total*100 if total>0 else 0:.1f}%)")
        self.logger.info(f"  Good (MSE<100, SSIM>0.90): {good} ({good/total*100 if total>0 else 0:.1f}%)")
        self.logger.info(f"  Acceptable (MSE<300, SSIM>0.80): {acceptable} ({acceptable/total*100 if total>0 else 0:.1f}%)")
        self.logger.info(f"  Needs Adjustment: {needs_fix} ({needs_fix/total*100 if total>0 else 0:.1f}%)")
        self.logger.info(f"  SUCCESS RATE: {success_rate:.1f}%")
        
        if success_rate >= 80:
            self.logger.info("  🎉 VALIDATION SUCCESSFUL")
        elif success_rate >= 60:
            self.logger.info("  ⚠️ PARTIAL VALIDATION")
        else:
            self.logger.info("  ❌ REQUIRES SIGNIFICANT ADJUSTMENTS")
        
        # Guardar reporte JSON detallado
        with open('validation_detailed_report.json', 'w') as f:
            json.dump({
                'metadata': {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'total_tests': total,
                    'success_rate': success_rate
                },
                'summary': {
                    'excellent': excellent, 'good': good, 
                    'acceptable': acceptable, 'needs_fix': needs_fix
                },
                'results': self.results
            }, f, indent=2)

if __name__ == "__main__":
    validator = SmartValidator()
    validator.validate_all_discovered()