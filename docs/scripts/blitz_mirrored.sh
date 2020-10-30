#!/bin/bash
# a wrapper script to run blitzloop on a multi-monitor systems
# where all monitors show the same output (mpv window). it is
# assumed that the browser window (to show and manipulate the
# playlist) is opened on external computer/smartphone
# 
# requires X11 as it uses xrandr
#
# things it does:
#  - save current monitor layout
#  - mirror all monitors (according to the one with greatest resolution)
#  - start blitzloop
#  - when blitzloop quits: restore the original layout
#
shopt -s lastpipe

echo "Saving current screen layout.."
original_layout=$(
xrandr | awk 'BEGIN {printf "xrandr"
                     orientation="normal"}
             $2 != "connected" { next }
             {if ($3 == "primary") {output=$1" --primary"
                                    modepan=$4
                                    if ($5 ~ /^(left|right|inverted)/) { orientation=$5 }
                                   }
                                   else
                                   {output=$1
                                    modepan=$3
                                    if ($4 ~ /^(left|right|inverted)/) { orientation=$4 }
                                   }}
             {mode=modepan
              sub(/\+.*/, "", mode)
              # strip offset from mode
             }
             {printf " --output %s --mode %s --scale 1 --panning %s --rotate %s",
                       output, mode, modepan, orientation} 
               END {print ""}'
)

# monitor with largest number of pixels will be used as a "master"
# others will mirror it
xrandr | sed 's/ primary / /' | grep connected | \
  perl -lane 'next unless @F[1] eq "connected";
              $res=$area=@F[2];
              $area =~ s/([0-9]+)x([0-9]+)\+.*/$1*$2/e;
              $res =~ s/\+.*//;
              printf "%s %s %s\n", $area, $res, @F[0]' | \
    sort -nrk 1 | head -1 | read _ master_resolution master_output

echo "master out: ${master_output} ($master_resolution)"

blitzloop_layout=$(
xrandr | sed 's/ primary / /' | awk -v master_out="${master_output}" -v master_res="${master_resolution}" '
   BEGIN {printf "xrandr "}
   $2 != "connected" || $1 == master_out { next } 
   { output=$1
     printf " --output %s --same-as %s --scale-from %s",
               output, master_out, master_res
   }
   END {print ""}
   '
)

${blitzloop_layout}

# add options if required (run blitzloop -h to list them)
blitzloop

echo "Restoring original screen layout.."
${original_layout}
