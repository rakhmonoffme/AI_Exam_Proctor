import numpy as np
import sounddevice as sd
from collections import deque
import time

class MultiSpeakerDetector:
    def __init__(self, rate=16000, chunk_duration=0.1, energy_threshold=0.01):
        """
        Initialize Multi-Speaker Detector
        
        Args:
            rate: Sample rate (Hz)
            chunk_duration: Audio chunk duration in seconds
            energy_threshold: Minimum energy to consider as speech
        """
        self.rate = rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(rate * chunk_duration)
        self.energy_threshold = energy_threshold
        
        # Track recent frequencies for speaker differentiation
        self.freq_history = deque(maxlen=10)
        
    def get_audio_features(self, audio_data):
        """Extract features from audio data"""
        
        # Flatten if stereo
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)
        
        # Calculate energy (RMS)
        energy = np.sqrt(np.mean(audio_data ** 2))
        
        # FFT for frequency analysis
        fft = np.fft.rfft(audio_data)
        freqs = np.fft.rfftfreq(len(audio_data), 1/self.rate)
        magnitudes = np.abs(fft)
        
        # Find dominant frequency (fundamental frequency)
        if len(magnitudes) > 0 and np.max(magnitudes) > 0:
            dominant_freq_idx = np.argmax(magnitudes)
            dominant_freq = freqs[dominant_freq_idx]
        else:
            dominant_freq = 0
        
        # Calculate spectral centroid
        if np.sum(magnitudes) > 0:
            spectral_centroid = np.sum(freqs * magnitudes) / np.sum(magnitudes)
        else:
            spectral_centroid = 0
        
        return {
            'energy': energy,
            'dominant_freq': dominant_freq,
            'spectral_centroid': spectral_centroid
        }
    
    def detect_multiple_speakers(self, features):
        """
        Detect if multiple speakers based on frequency variation
        
        Args:
            features: Audio features dict
            
        Returns:
            bool: True if multiple speakers detected
        """
        if features['energy'] < self.energy_threshold:
            return False  # No speech detected
        
        # Add to history
        self.freq_history.append(features['dominant_freq'])
        
        if len(self.freq_history) < 5:
            return False  # Not enough data
        
        # Calculate frequency variation
        freq_std = np.std(list(self.freq_history))
        
        # High variation suggests multiple speakers
        # Typical single speaker: std < 50 Hz
        # Multiple speakers: std > 80 Hz
        return freq_std > 80
    
    def analyze(self, duration=30):
        """
        Analyze audio for multiple speakers
        
        Args:
            duration: Analysis duration in seconds
            
        Returns:
            dict: Analysis results
        """
        print(f"Recording for {duration} seconds...")
        
        # Record audio
        audio_data = sd.rec(
            int(duration * self.rate),
            samplerate=self.rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()  # Wait until recording is finished
        
        # Process in chunks
        num_chunks = int(duration / self.chunk_duration)
        multi_speaker_count = 0
        total_speech_frames = 0
        
        print("Analyzing audio...")
        
        for i in range(num_chunks):
            start_idx = int(i * self.chunk_size)
            end_idx = int((i + 1) * self.chunk_size)
            chunk = audio_data[start_idx:end_idx, 0]
            
            # Extract features
            features = self.get_audio_features(chunk)
            
            # Detect multiple speakers
            is_multi = self.detect_multiple_speakers(features)
            
            if features['energy'] > self.energy_threshold:
                total_speech_frames += 1
                if is_multi:
                    multi_speaker_count += 1
                
                status = "MULTIPLE" if is_multi else "SINGLE"
                print(f"Chunk {i+1}/{num_chunks} | Energy: {features['energy']:.3f} | Freq: {features['dominant_freq']:.1f} Hz | {status}")
        
        # Calculate results
        multiple_speaker_ratio = multi_speaker_count / total_speech_frames if total_speech_frames > 0 else 0
        
        return {
            'multiple_speakers_detected': multiple_speaker_ratio > 0.3,
            'confidence': multiple_speaker_ratio,
            'total_speech_frames': total_speech_frames
        }
    
    def analyze_realtime(self, duration=30, callback=None):
        """
        Real-time analysis with callback
        
        Args:
            duration: Analysis duration in seconds
            callback: Function to call with results (optional)
        """
        multi_speaker_count = 0
        total_speech_frames = 0
        
        def audio_callback(indata, frames, time_info, status):
            nonlocal multi_speaker_count, total_speech_frames
            
            if status:
                print(f"Status: {status}")
            
            # Extract features
            audio_chunk = indata[:, 0] if len(indata.shape) > 1 else indata
            features = self.get_audio_features(audio_chunk)
            
            # Detect multiple speakers
            is_multi = self.detect_multiple_speakers(features)
            
            if features['energy'] > self.energy_threshold:
                total_speech_frames += 1
                if is_multi:
                    multi_speaker_count += 1
                
                result = {
                    'is_multiple': is_multi,
                    'energy': features['energy'],
                    'freq': features['dominant_freq']
                }
                
                if callback:
                    callback(result)
                else:
                    status = "MULTIPLE" if is_multi else "SINGLE"
                    print(f"Energy: {features['energy']:.3f} | Freq: {features['dominant_freq']:.1f} Hz | {status}")
        
        print(f"Starting real-time analysis for {duration} seconds...")
        
        with sd.InputStream(callback=audio_callback, channels=1, samplerate=self.rate):
            sd.sleep(int(duration * 1000))
        
        multiple_speaker_ratio = multi_speaker_count / total_speech_frames if total_speech_frames > 0 else 0
        
        return {
            'multiple_speakers_detected': multiple_speaker_ratio > 0.3,
            'confidence': multiple_speaker_ratio,
            'total_speech_frames': total_speech_frames
        }


# Standalone function version
def detect_multiple_speakers_simple(duration=10, energy_threshold=0.01):
    """
    Simple function to detect multiple speakers
    
    Args:
        duration: Recording duration in seconds
        energy_threshold: Minimum energy for speech
        
    Returns:
        dict: Detection results
    """
    detector = MultiSpeakerDetector(energy_threshold=energy_threshold)
    result = detector.analyze(duration)
    return result


# Example usage
if __name__ == "__main__":
    # Using class
    detector = MultiSpeakerDetector(energy_threshold=0.01)
    
    # Method 1: Record then analyze
    result = detector.analyze(duration=30)
    
    print("\n" + "="*50)
    print("Analysis Results:")
    print(f"Multiple Speakers: {result['multiple_speakers_detected']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Speech Frames: {result['total_speech_frames']}")
    print("="*50)
    
    # Method 2: Real-time analysis
    # result = detector.analyze_realtime(duration=30)
    
    # Using simple function
    # result = detect_multiple_speakers_simple(duration=5)
    # print(f"Multiple speakers: {result['multiple_speakers_detected']}")