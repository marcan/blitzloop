var app = angular.module('karaoke', [
    'translate',
    'translate.directives',
]);

function nudge() {
    var foo = angular.element('<style></style>');
    angular.element(document.body).append(foo);
    foo.remove();
    console.log("nudged");
}

app.directive('slider', function($document){
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        scope: {
            value: "=ngModel",
        },
        template:
            '<div class="slider"><div class="label" ng-transclude translate></div>' +
                '<div class="value"><div>' +
                    '<div>{{valueLabel}}</div>' +
                '</div></div>' +
                '<div class="outer"><div class="bar"><div class="chunk"></div><div class="knob"></div></div></div>' +
            '</div>',
        link: function(scope, element, attrs) {
            attrs.min = parseFloat(attrs.min);
            attrs.max = parseFloat(attrs.max);
            var outer = angular.element(element.children()[2]);
            var bar = angular.element(outer.children()[0]);
            var knob = angular.element(bar.children()[1]);
            var chunk = angular.element(bar.children()[0]);

            if ('ontouchend' in document) {
                knob.bind('touchstart', touchstart);
                outer.bind('touchstart', touchstart);
            } else {
                knob.bind('mousedown', down);
            }

            var touchHandled = false;

            function down(e) {
                e.returnValue = false;
                $document.bind('mouseup', up);
                $document.bind('mousemove', move);
                return;
            }

            function up() {
                $document.unbind('mouseup', up);
                $document.unbind('mousemove', move);
            }

            function touchstart(e) {
                if (touchHandled) {
                    return;
                }
                e.returnValue = false;
                e.preventDefault = true;
                touchHandled = true;
                $document.bind('touchend', touchend);
                $document.bind('touchmove', touchmove);
                $document.bind('touchcancel', touchend);
                move(e.touches[0]);
            }

            function touchend(e) {
                touchHandled = false;
                $document.unbind('touchend', touchend);
                $document.unbind('touchmove', touchmove);
                $document.unbind('touchcancel', touchend);
            }

            function touchmove(e) {
                if (!touchHandled) {
                    return;
                }
                if (e.touches.length > 1) {
                    return;
                }
                move(e.touches[0]);
            }

            function move(e) {
                var x1 = bar[0].offsetLeft;
                var x2 = x1 + bar[0].offsetWidth;
                var pos = (e.clientX - x1) / (x2 - x1);
                if (pos < 0) { pos = 0; }
                if (pos > 1) { pos = 1; }
                var val = Math.round(pos * (attrs.max - attrs.min) + attrs.min);
                if (scope.value != val) {
                    scope.$apply(function() {
                        scope.value = val;
                    });
                }
            }

            function pos(v) {
                return 100 * (v - attrs.min) / (attrs.max - attrs.min);
            }

            scope.$watch("value", function(value) {
                knob.css('left', pos(value)+'%')
                if (value < 0) {
                    var end = pos(Math.min(0, attrs.max));
                    chunk.css('left', pos(value)+'%');
                    chunk.css('width', (end-pos(value))+'%');
                } else {
                    var end = pos(Math.max(0, attrs.min));
                    chunk.css('left', end+'%');
                    chunk.css('width', (pos(value)-end)+'%');
                }
                knob.css('left', pos(value)+'%');
                if ('plus' in attrs && value > 0) {
                    scope.valueLabel = '+' + value;
                } else {
                    scope.valueLabel = value;
                }
            });
        }
    }
});

app.run(['translate', function(translate) {
    translate.add(g_i18n);
}]);

app.controller('MenuCtrl', function($scope, $rootScope, $http) {
    $rootScope.tab = "";
    $scope.lang = g_cfg.lang;
    $scope.latin = g_cfg.latin;
    $scope.setLang = function(lang) {
        $http.get('/cfg/lang/' + lang).success(function(data) {
            location.reload();
        });
    };
    $scope.setLatin = function(latin) {
        $http.get('/cfg/latin/' + (0+latin)).success(function(data) {
            $scope.latin = 0+latin;
            $rootScope.$broadcast('latinChanged', 0+latin)
        });
    };
});

app.controller('SongListCtrl', function($scope, $rootScope, $http) {
    $rootScope.tab = "songs";
    $scope.refresh = function() {
        $http.get('/songlist').success(function(data) {
            for (var i = 0; i < data.songs.length; i++) {
                data.songs[i].coverUrl = "/song/" + data.songs[i].id + "/cover/105" + "?" + g_cfg.nonce;
                data.songs[i].link = "#/songs/" + data.songs[i].id
            }
            $scope.songs = data.songs;
            nudge(); // WTF webkit
        });
    };
    $scope.$on('latinChanged', function(e, arg){
        $scope.refresh();
    });
    $scope.refresh();
});

app.controller('QueueListCtrl', function($scope, $rootScope, $http, $timeout) {
    $rootScope.tab = "queue";
    $scope.dead = 0;
    $scope.refresh = function() {
        $http.get('/queue').success(function(data) {
            for (var i = 0; i < data.queue.length; i++) {
                data.queue[i].coverUrl = "/song/" + data.queue[i].id + "/cover/105" + "?" + g_cfg.nonce;
                if (i == 0) {
                    data.queue[i].link = "#/queue/now"
                } else {
                    data.queue[i].link = "#/queue/" + data.queue[i].qid
                }
            }
            $scope.songs = data.queue;
            nudge(); // WTF webkit
        });
    };
    poll = function() {
        $scope.refresh();
        if (!$scope.dead) {
            $scope.refresh_promise = $timeout(poll, 3000);
        }
    };
    $scope.$on('latinChanged', function(e, arg){
        $scope.refresh();
    });
    $scope.$on('$destroy',function(){
        $timeout.cancel($scope.refresh_promise);
        $scope.dead = 1;
    });
    poll();
});

app.controller('SongDetailCtrl', function($scope, $rootScope, $routeParams, $http, $location) {
    $rootScope.tab = "songs";
    $scope.loaded = false;
    $scope.refresh = function() {
        $http.get('/song/' + $routeParams.songId).success(function(data) {
            $scope.song = data;
            $scope.coverUrl = "/song/" + data.id + "/cover/200" + "?" + g_cfg.nonce;
            $scope.song.config = {
                variant: 0,
                channels: [3],
                speed: 0,
                pitch: 0,
                pause: false
            };
            for (var i = 0; i < data.variants.length; i++) {
                if (data.variants[i].default) {
                    $scope.song.config.variant = i;
                    break;
                }
            }
            $scope.variant = data.variants[$scope.song.config.variant];
            if (!$scope.loaded) {
                nudge(); // WTF webkit
            }
            $scope.loaded = true;
        });
    };
    $scope.$on('latinChanged', function(e, arg){
        var song_config = $scope.song.config;
        $scope.refresh();
        $scope.song.config = song_config;
    });
    $scope.$watch("song.config.variant", function(value) {
        if (value === undefined) {
            return;
        }
        $scope.variant = $scope.song.variants[$scope.song.config.variant];
    });
    $scope.addToQueue = function() {
        $http.post('/queue/add/' + $routeParams.songId, $scope.song.config).success(function(data) {
            $location.path("/queue/" + data.qid + "/new")
        });
    };
    $scope.refresh();
});

app.controller('QueueEntryCtrl', function($scope, $rootScope, $routeParams, $http, $location, $timeout, $route) {
    $rootScope.tab = "queue";
    if ($routeParams.qid == "now") {
        $rootScope.tab = "now";
    }
    $scope.backUrl = $route.current.back;
    $scope.dirty = false;
    $scope.posting = false;
    $scope.loaded = false;
    $scope.refresh = function() {
        if ($scope.posting) {
            return;
        }
        $scope.getValid = true;
        $http.get('/queue/' + $routeParams.qid).success(function(data) {
            if (!$scope.getValid) {
                return;
            }
            $scope.song = data;
            $scope.coverUrl = "/song/" + data.id + "/cover/200" + "?" + g_cfg.nonce;
            $scope.variant = data.variants[$scope.song.config.variant];
            if (data.idx == 0) {
                $location.path("/queue/now")
            }
            $scope.serverConfig = angular.toJson($scope.song.config);
            $scope.loaded = true;
            nudge();
        }).error(function(data) {
            $location.path("/queue")
        });
    };
    poll = function() {
        $scope.refresh();
        $scope.refresh_promise = $timeout(poll, 3000);
    };
    $scope.$on('latinChanged', function(e, arg){
        $scope.refresh();
    });
    $scope.post = function() {
        $scope.posting = true;
        $scope.getValid = false;
        $scope.serverConfig = angular.toJson($scope.song.config);
        $http.post('/queue/change/' + $scope.song.qid, $scope.song.config).success(function(data) {
            if ($scope.dirty) {
                $scope.dirty = false;
                $scope.post()
            } else {
                $scope.posting = false;
            }
        }).error(function(data) {
            $scope.posting = false;
            $scope.refresh();
        });
    };
    $scope.$watch("song.config", function(value) {
        if (value === undefined) {
            return;
        }
        if (angular.toJson($scope.song.config) != $scope.serverConfig) {
            if (!$scope.posting) {
                $scope.post();
            } else {
                $scope.dirty = true;
            }
        }
        if ($scope.variant.id != $scope.song.config.variant) {
            $scope.variant = $scope.song.variants[$scope.song.config.variant];
        }
    }, true);
    $scope.seek = function(offset) {
        $http.post('/queue/now/seek', {"offset": offset});
    };
    $scope.seekto = function(pos) {
        $http.post('/queue/now/seek', {"position": pos});
    };
    $scope.removeFromQueue = function() {
        $http.post('/queue/remove/' + $scope.song.qid).success(function(data) {
            if ($routeParams.qid == "now") {
                $scope.refresh();
            } else if ($scope.backUrl == "/queue") {
                $location.path("/queue")
            } else {
                $location.path("/songs/" + $scope.song.id)
            }
        }).error(function(data) {
            $scope.refresh();
        });;
    };
    $scope.$on('$destroy',function(){
        $timeout.cancel($scope.refresh_promise);
    });
    poll();
});

app.controller('SettingsCtrl', function($scope, $rootScope, $routeParams, $http, $location, $timeout, $route) {
    $rootScope.tab = "settings";
    $scope.dirty = false;
    $scope.posting = false;
    $scope.loaded = false;
    $scope.refresh = function() {
        if ($scope.posting) {
            return;
        }
        $scope.getValid = true;
        $http.get('/settings').success(function(data) {
            if (!$scope.getValid) {
                return;
            }
            $scope.settings = data;
            $scope.serverSettings = angular.toJson($scope.settings);
            $scope.loaded = true;
            $nudge();
        }).error(function(data) {
            $location.path("/settings")
        });
    };
    poll = function() {
        $scope.refresh();
        $scope.refresh_promise = $timeout(poll, 3000);
    };
    $scope.post = function() {
        $scope.posting = true;
        $scope.getValid = false;
        $scope.serverSettings = angular.toJson($scope.settings);
        $http.post('/settings/change', $scope.settings).success(function(data) {
            if ($scope.dirty) {
                $scope.dirty = false;
                $scope.post()
            } else {
                $scope.posting = false;
            }
        }).error(function(data) {
            $scope.posting = false;
            $scope.refresh();
        });
    };
    $scope.$watch("settings", function(value) {
        if (value === undefined) {
            return;
        }
        if (angular.toJson($scope.settings) != $scope.serverSettings) {
            if (!$scope.posting) {
                $scope.post();
            } else {
                $scope.dirty = true;
            }
        }
    }, true);
    $scope.$on('$destroy',function(){
        $timeout.cancel($scope.refresh_promise);
    });
    $scope.reset = function() {
        $scope.settings.volume = 50;
        $scope.settings.headstart = 30;
        $scope.settings.mic_volume = 80;
        $scope.settings.mic_feedback = 20;
        $scope.settings.mic_delay = 12;
    }
    poll();
});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.
        when('/songs', {templateUrl: 's/partials/song-list.html',   controller: 'SongListCtrl'}).
        when('/songs/:songId', {templateUrl: 's/partials/song.html', controller: 'SongDetailCtrl', back: '/songs'}).
        when('/queue', {templateUrl: 's/partials/song-list.html',   controller: 'QueueListCtrl'}).
        when('/queue/:qid', {templateUrl: 's/partials/song.html', controller: 'QueueEntryCtrl', back: '/queue'}).
        when('/queue/:qid/new', {templateUrl: 's/partials/song.html', controller: 'QueueEntryCtrl', back: '/songs'}).
        when('/settings', {templateUrl: 's/partials/settings.html', controller: 'SettingsCtrl'}).
        otherwise({redirectTo: '/songs'});
}]);

