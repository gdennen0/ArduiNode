#!/usr/bin/env python3
"""
Diagnostic script to identify performance bottlenecks
"""

import time
import sys
import config

def test_timing_precision():
    """Test system timing precision"""
    print("Testing timing precision...")
    
    # Test time.sleep() accuracy
    target = 0.01  # 10ms
    samples = 100
    errors = []
    
    for _ in range(samples):
        start = time.perf_counter()
        time.sleep(target)
        actual = time.perf_counter() - start
        errors.append(abs(actual - target))
    
    avg_error = sum(errors) / len(errors) * 1000  # Convert to ms
    max_error = max(errors) * 1000
    
    print(f"  Target sleep: {target*1000:.1f}ms")
    print(f"  Average error: {avg_error:.3f}ms")
    print(f"  Max error: {max_error:.3f}ms")
    
    if avg_error > 1.0:
        print("  WARNING: High timing jitter detected")
        print("  This may cause frame drops")
    else:
        print("  ✓ Timing precision is good")
    
    return avg_error < 1.0

def test_frame_generation_speed():
    """Test how fast we can generate test frames"""
    print("\nTesting frame generation speed...")
    
    test_duration = 1.0
    frame_count = 0
    start = time.perf_counter()
    
    while (time.perf_counter() - start) < test_duration:
        # Generate a test frame
        data = [128] * config.DMX_CHANNELS
        frame_count += 1
    
    fps = frame_count / test_duration
    print(f"  Generated {frame_count} frames in {test_duration}s")
    print(f"  Frame generation rate: {fps:.1f} FPS")
    
    if fps < config.OUTPUT_FPS * 2:
        print(f"  WARNING: Frame generation is too slow")
        print(f"  Need at least {config.OUTPUT_FPS * 2} FPS")
    else:
        print(f"  ✓ Frame generation speed is adequate")
    
    return fps >= config.OUTPUT_FPS * 2

def test_serial_write_speed():
    """Test serial write speed"""
    print("\nTesting serial write speed...")
    
    try:
        import serial
        
        # Try to open serial port
        try:
            ser = serial.Serial(
                config.ARDUINO_PORT,
                config.ARDUINO_BAUD,
                timeout=1,
                write_timeout=0.1
            )
            
            # Test write speed
            test_duration = 1.0
            frame_count = 0
            start = time.perf_counter()
            
            # Create a test packet
            packet = bytearray(3 + config.DMX_CHANNELS)
            packet[0] = 0xFF
            packet[1] = config.DMX_CHANNELS & 0xFF
            packet[2] = (config.DMX_CHANNELS >> 8) & 0xFF
            packet[3:] = [128] * config.DMX_CHANNELS
            
            while (time.perf_counter() - start) < test_duration:
                ser.write(packet)
                frame_count += 1
            
            elapsed = time.perf_counter() - start
            fps = frame_count / elapsed
            
            ser.close()
            
            print(f"  Sent {frame_count} frames in {elapsed:.2f}s")
            print(f"  Serial write rate: {fps:.1f} FPS")
            print(f"  Bytes per frame: {len(packet)} bytes")
            print(f"  Throughput: {(len(packet) * fps / 1024):.1f} KB/s")
            
            if fps < config.OUTPUT_FPS:
                print(f"  WARNING: Serial write is too slow")
                print(f"  Need at least {config.OUTPUT_FPS} FPS")
                print(f"  Consider increasing baud rate or reducing channels")
            else:
                print(f"  ✓ Serial write speed is adequate")
            
            return fps >= config.OUTPUT_FPS
            
        except serial.SerialException as e:
            print(f"  ✗ Could not open serial port: {e}")
            print(f"  Skipping serial write test")
            return None
            
    except ImportError:
        print("  ✗ pyserial not installed")
        return None

def test_queue_performance():
    """Test queue performance"""
    print("\nTesting queue performance...")
    
    import queue
    import threading
    
    test_queue = queue.Queue(maxsize=config.FRAME_BUFFER_SIZE)
    
    # Producer thread
    def producer():
        for i in range(1000):
            try:
                test_queue.put_nowait([128] * config.DMX_CHANNELS)
            except queue.Full:
                pass
    
    # Consumer thread
    consumed = [0]
    def consumer():
        while consumed[0] < 1000:
            try:
                test_queue.get_nowait()
                consumed[0] += 1
            except queue.Empty:
                time.sleep(0.0001)
    
    start = time.perf_counter()
    
    prod_thread = threading.Thread(target=producer)
    cons_thread = threading.Thread(target=consumer)
    
    prod_thread.start()
    cons_thread.start()
    
    prod_thread.join()
    cons_thread.join()
    
    elapsed = time.perf_counter() - start
    ops_per_sec = 1000 / elapsed
    
    print(f"  Processed 1000 frames in {elapsed:.3f}s")
    print(f"  Queue throughput: {ops_per_sec:.1f} ops/s")
    
    if ops_per_sec < config.OUTPUT_FPS * 2:
        print(f"  WARNING: Queue performance is marginal")
    else:
        print(f"  ✓ Queue performance is good")
    
    return ops_per_sec >= config.OUTPUT_FPS * 2

def test_cpu_usage():
    """Check system CPU availability"""
    print("\nChecking system resources...")
    
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        mem_percent = psutil.virtual_memory().percent
        
        print(f"  CPU usage: {cpu_percent:.1f}%")
        print(f"  Memory usage: {mem_percent:.1f}%")
        
        if cpu_percent > 80:
            print("  WARNING: High CPU usage detected")
            print("  May impact performance")
        
        if mem_percent > 80:
            print("  WARNING: High memory usage detected")
        
        return cpu_percent < 80 and mem_percent < 80
        
    except ImportError:
        print("  psutil not installed - skipping resource check")
        return None

def main():
    """Run all diagnostics"""
    print("="*60)
    print("DMX Bridge Performance Diagnostics")
    print("="*60)
    
    print(f"\nConfiguration:")
    print(f"  Output FPS: {config.OUTPUT_FPS}")
    print(f"  DMX Channels: {config.DMX_CHANNELS}")
    print(f"  Buffer Size: {config.FRAME_BUFFER_SIZE}")
    print(f"  Baud Rate: {config.ARDUINO_BAUD}")
    
    results = []
    
    results.append(("Timing Precision", test_timing_precision()))
    results.append(("Frame Generation", test_frame_generation_speed()))
    results.append(("Queue Performance", test_queue_performance()))
    results.append(("Serial Write Speed", test_serial_write_speed()))
    results.append(("System Resources", test_cpu_usage()))
    
    print("\n" + "="*60)
    print("Diagnostic Summary:")
    print("="*60)
    
    for name, result in results:
        if result is None:
            status = "SKIP"
        elif result:
            status = "PASS"
        else:
            status = "FAIL"
        print(f"  {name:20}: {status}")
    
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\n⚠ Performance issues detected")
        print("\nRecommendations:")
        if any(name == "Serial Write Speed" and not result for name, result in results):
            print("  - Increase ARDUINO_BAUD in config.py")
            print("  - Reduce DMX_CHANNELS if not all are needed")
        if any(name == "Timing Precision" and not result for name, result in results):
            print("  - Close background applications")
            print("  - Consider using a real-time OS")
        print("  - Increase FRAME_BUFFER_SIZE in config.py")
    else:
        print("\n✓ System performance looks good!")
        print("  The DMX bridge should run efficiently")

if __name__ == '__main__':
    main()

