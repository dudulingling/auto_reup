UPDATE video_history SET raw_video_path = REPLACE(raw_video_path, 'data/data/', 'data/') WHERE raw_video_path LIKE '%data/data/%';
UPDATE video_history SET srt_origin_path = REPLACE(srt_origin_path, 'data/data/', 'data/') WHERE srt_origin_path LIKE '%data/data/%';
UPDATE video_history SET srt_translated_path = REPLACE(srt_translated_path, 'data/data/', 'data/') WHERE srt_translated_path LIKE '%data/data/%';
UPDATE video_history SET audio_tts_path = REPLACE(audio_tts_path, 'data/data/', 'data/') WHERE audio_tts_path LIKE '%data/data/%';
UPDATE video_history SET final_video_path = REPLACE(final_video_path, 'data/data/', 'data/') WHERE final_video_path LIKE '%data/data/%';

UPDATE video_history SET raw_video_path = REPLACE(raw_video_path, 'data\data\', 'data\') WHERE raw_video_path LIKE '%data\data\%';
UPDATE video_history SET srt_origin_path = REPLACE(srt_origin_path, 'data\data\', 'data\') WHERE srt_origin_path LIKE '%data\data\%';
UPDATE video_history SET srt_translated_path = REPLACE(srt_translated_path, 'data\data\', 'data\') WHERE srt_translated_path LIKE '%data\data\%';
UPDATE video_history SET audio_tts_path = REPLACE(audio_tts_path, 'data\data\', 'data\') WHERE audio_tts_path LIKE '%data\data\%';
UPDATE video_history SET final_video_path = REPLACE(final_video_path, 'data\data\', 'data\') WHERE final_video_path LIKE '%data\data\%';
