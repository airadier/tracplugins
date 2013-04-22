function makeFavourite(url)
{
    elem = $('#favimg');
    src = elem.attr('src');
    if (src.substring(src.length - 8) == 'favn.png') {
        src = src.replace(/favn.png$/, 'favy.png');       
        jQuery.get(url, {'favourite': 1});
    } else {
        src = src.replace(/favy.png$/, 'favn.png');
        jQuery.get(url, {'favourite': 0});
    }
    
    elem.attr('src', src);
}
