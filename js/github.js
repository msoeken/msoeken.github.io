$.getJSON( "https://api.github.com/users/msoeken/events/public", function( data ) {
    var count = 0;
    var index = 0;
    while ( true ) {
        var event = data[index];
        index = index + 1;

        if ( event.type != "PushEvent" ) continue;
        if ( !event.repo.name.startsWith( "msoeken" ) ) continue;

        repo = event.repo.name.substring( 8 );
        console.log( repo );

        if ( !( repo == "alice" || repo == "cirkit" || repo == "kitty" || repo == "pat" ) ) continue;

        var commits = event.payload.commits;

        var time = jQuery.timeago( event.created_at );
        for ( var i = 0; i < commits.length; ++i ) {
            $.getJSON( commits[i].url, function( commit_data ) {
                var commit = commit_data.commit;
                var msg = commit.message;
                var author = commit.author.name;
                var time = jQuery.timeago( commit.author.date );
                var url = commit_data.html_url;
                $("ul#commits").append( '<li class="list-group-item"><img src="images/' + repo + '.svg" style="width: 24pt; padding-left: 5pt" class="pull-right" /><p>' + msg + '</p><p><a href="' + url + '" target="_blank">comitted ' + time + '</a> to <a href="https://github.com/msoeken/' + repo + '" target="_blank">' + repo + '</a></p></li>' );
            } );

            count = count + 1;
            if ( count == 10 ) break;
        }

        if ( count == 10 ) break;
    }
} );

