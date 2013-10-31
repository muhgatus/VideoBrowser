/*
This file is part of VideoBrowser.

Copyright (C) 2013   Sven Ludwig aka muhgatus

VideoBrowser is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

VideoBrowser is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with VideoBrowser.  If not, see <http://www.gnu.org/licenses/>.
*/

jQuery.expr[':'].regex = function(elem, index, match) {
  var matchParams = match[3].split(','),
    validLabels = /^(data|css):/,
    attr = {
      method: matchParams[0].match(validLabels) ? 
              matchParams[0].split(':')[0] : 'attr',
      property: matchParams.shift().replace(validLabels,'')
    },
    regexFlags = 'ig',
    regex = new RegExp(matchParams.join('').replace(/^\s+|\s+$/g,''), regexFlags);
  return regex.test(jQuery(elem)[attr.method](attr.property));
}

function enable_multi() {
  $(':regex(id, ^multi)').prop('href','#').css({"opacity" : "1"});
}
function disable_multi() {
  $(':regex(id, ^multi)').prop('href',null).css({"opacity" : "0.3", "cursor":"default"});
}

$(document).ready(function(){
  $('.videofile').each(function() {
    $(this).append('<input class="multidelete" type="checkbox" style="display: none;">').click(function () {
      if ( $(this).children('input').prop('checked') ) {
        $(this).css('background', '#eee');
        $(this).children('input').prop('checked', false);
      } else {
        $(this).css('background', '#fee');
        $(this).children('input').prop('checked', true);
      }
      if ( $('.multidelete:checked').length == 0 ) {
        disable_multi();
      } else {
        enable_multi();
      }
    });
  });
  $('#toolbar').append(' Multi: [<a id="multidelete">delete</a>]')
  $('#toolbar').append(' [<a id="multiplaylist">playlist</a>]')
  $('#toolbar').append(' [<a id="multiclear">clear</a>]')
  $('#toolbar').append(' Switch: [<a id="switch_downloadmode" href="#">to file mode</a><input type="checkbox" id="downloadmode" checked>]')
  disable_multi();
  $('#multidelete').click(function() {
    var data=new Array();
    $('.videofile').each(function() {
      var href=$(this).find('a').prop('href').replace(/[?].*/,'');
      if ( $(this).children('input').prop('checked') ) {
        data.push(decodeURIComponent(href.replace(/^http.*\/hts\//,'')));
      }
    });
    if ( data.length == 0 ) return;
    data=JSON.stringify(data);
    data=$.base64.encode(data);
    window.location = '/video/delete?delete_key='+encodeURIComponent(data);
  });
  $('#multiplaylist').click(function() {
    var data=new Array();
    $('.videofile').each(function() {
      var href=$(this).find('a').prop('href').replace(/[?].*/,'');
      if ( $(this).children('input').prop('checked') ) {
        data.push(decodeURIComponent(href.replace(/^http.*\/hts\//,'')));
      }
    });
    if ( data.length == 0 ) return;
    data=JSON.stringify(data);
    data=$.base64.encode(data);
    window.location = '/video/playlist?files='+encodeURIComponent(data);
    $('#multiclear').click();
  });
  $('#multiclear').click(function() {
    $('.videofile input:checked').each(function() {
      $(this).parent().css('background','#eee');
      $(this).prop('checked',false);
    });
    disable_multi();
  });
  $('#downloadmode').change(function() {
    var append='';
    if ( $(this).prop('checked') ) {
      append='?mode=playlist';
      $('#switch_downloadmode').text('to file mode');
    } else {
      append='?mode=file';
      $('#switch_downloadmode').text('to playlist mode');
    }
    $('.videofile a').each(function() {
      var href=$(this).prop('href').replace(/[?].*/,'');
      $(this).prop('href', href+append);
    });
  }).css('display','none');
  $('#switch_downloadmode').click(function() {
    $('#downloadmode').click();
  });
});
