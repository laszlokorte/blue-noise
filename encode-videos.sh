ffmpeg  -framerate 1 -i "output/frames/p01-s03-after-swap/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p01-s03-after-swap.mp4
ffmpeg  -framerate 1 -i "output/frames/p01-s03-before-swap/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p01-s03-before-swap.mp4
ffmpeg  -framerate 1 -i "output/frames/p01-s03-blurred/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p01-s03-blurred.mp4
ffmpeg  -framerate 1 -i "output/frames/p01-s03-blurred_dense_masked/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p01-s03-blurred_dense_masked.mp4
ffmpeg  -framerate 1 -i "output/frames/p01-s03-blurred_voidest_offset/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p01-s03-blurred_voidest_offset.mp4
ffmpeg  -framerate 1 -i "output/frames/p02-s01-after-ranks/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p02-s01-after-ranks.mp4
ffmpeg  -framerate 1 -i "output/frames/p02-s01-after-remove/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p02-s01-after-remove.mp4
ffmpeg  -framerate 1 -i "output/frames/p02-s01-before-remove/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p02-s01-before-remove.mp4
ffmpeg  -framerate 1 -i "output/frames/p02-s01-blurred/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p02-s01-blurred.mp4
ffmpeg  -framerate 1 -i "output/frames/p02-s01-blurred_dense_masked/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p02-s01-blurred_dense_masked.mp4
ffmpeg  -framerate 1 -i "output/frames/p02-s01-blurred_dense_restricted/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p02-s01-blurred_dense_restricted.mp4
ffmpeg  -framerate 1 -i "output/frames/p03-s01-after-new/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p03-s01-after-new.mp4
ffmpeg  -framerate 1 -i "output/frames/p03-s01-after-ranks/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p03-s01-after-ranks.mp4
ffmpeg  -framerate 1 -i "output/frames/p03-s01-before-new/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p03-s01-before-new.mp4
ffmpeg  -framerate 1 -i "output/frames/p03-s01-blurred/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p03-s01-blurred.mp4
ffmpeg  -framerate 1 -i "output/frames/p03-s01-blurred_voidest_offset/%4d.png"  -vf scale=64:-1  -sws_flags neighbor -c:v libx264  -x264opts "keyint=1" -r 1 -pix_fmt yuv420p public/steps/p03-s01-blurred_voidest_offset.mp4

copy output/recording.json public/steps/recording.json
copy output/frames/*.png public/steps/ 