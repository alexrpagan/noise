noise
=====

Simply select a WAV file with the sound to repeat:

  python noise.py noise.wav
  
Noise will adaptively adjust the volume of the noise sample based on the level of ambient noise in the room.

TODOS:

- smoothing for volume changes
- better model for detecting periods of relative noisiness (e.g., conversation)
- parameter tuning

