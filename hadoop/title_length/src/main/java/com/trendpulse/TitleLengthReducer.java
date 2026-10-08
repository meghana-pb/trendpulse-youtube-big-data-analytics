package com.trendpulse;
import org.apache.hadoop.io.Text; import org.apache.hadoop.mapreduce.Reducer; import java.io.IOException;
/** Title Length Reducer. Output: bucket TAB count|avg_views|avg_engagement|avg_trending */
public class TitleLengthReducer extends Reducer<Text,Text,Text,Text> {
    @Override public void reduce(Text key, Iterable<Text> values, Context ctx) throws IOException,InterruptedException {
        long cnt=0,tv=0; double te=0,tt=0;
        for(Text v:values){String[] p=v.toString().split("\\|");if(p.length<3)continue;
            try{tv+=Long.parseLong(p[0]);te+=Double.parseDouble(p[1]);tt+=Integer.parseInt(p[2]);cnt++;}catch(Exception e){}}
        if(cnt==0)return;
        ctx.write(key,new Text(String.format("%d|%.2f|%.6f|%.2f",cnt,(double)tv/cnt,te/cnt,tt/cnt)));
    }
}
