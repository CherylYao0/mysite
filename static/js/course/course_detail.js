$(function () {
  let $course_data = $(".course-data");
  let sVideoUrl = $course_data.data('video-url');
  let sCoverUrl = $course_data.data('cover-url');

  let player = cyberplayer("course-video").setup({
    width: '100%',
    height: 650,
    file: sVideoUrl,
    image: sCoverUrl,
    autostart: false,
    stretching: "uniform",
    repeat: false,
    volume: 100,
    controls: true,
    ak: '13704a0227944e89a1257f53a27138d9'
  });

});