package com.trendpulse;
import org.apache.hadoop.io.Text; import org.apache.hadoop.mapreduce.Reducer; import java.io.IOException;
/** Engagement Reducer. Output: bucket TAB count|avg_views|avg_likes|avg_comments|avg_trending */
public class EngagementReducer extends Reducer<Text,Text,Text,Text> {
    @Override public void reduce(Text key, Iterable<Text> values, Context ctx) throws IOException,InterruptedException {
        long cnt=0,tv=0,tl=0,tc=0; double tt=0;
        for(Text v:values){String[] p=v.toString().split("\\|");if(p.length<4)continue;
            try{tv+=Long.parseLong(p[0]);tl+=Long.parseLong(p[1]);tc+=Long.parseLong(p[2]);tt+=Integer.parseInt(p[3]);cnt++;}catch(Exception e){}}
        if(cnt==0)return;
        ctx.write(key,new Text(String.format("%d|%.2f|%.2f|%.2f|%.2f",cnt,(double)tv/cnt,(double)tl/cnt,(double)tc/cnt,tt/cnt)));
    }
}
