package com.trendpulse;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;
import java.io.IOException;

/** TrendPulse - Upload Time Reducer. Output: hour TAB count|avg_views|avg_engagement|avg_trending|bucket */
public class UploadTimeReducer extends Reducer<Text, Text, Text, Text> {
    @Override
    public void reduce(Text key, Iterable<Text> values, Context context) throws IOException, InterruptedException {
        long count=0, totalViews=0; double totalEng=0,totalTrend=0; int maxTrend=0; String bucket="Unknown";
        for(Text val:values){
            String[] p=val.toString().split("\\|"); if(p.length<4) continue;
            try{
                totalViews+=Long.parseLong(p[0]); totalEng+=Double.parseDouble(p[1]);
                int td=Integer.parseInt(p[2]); totalTrend+=td; if(td>maxTrend)maxTrend=td;
                if(p.length>3&&!p[3].isEmpty()) bucket=p[3]; count++;
            }catch(Exception e){}
        }
        if(count==0) return;
        String result=String.format("%d|%.2f|%.6f|%.2f|%d|%s",count,
                (double)totalViews/count,totalEng/count,totalTrend/count,maxTrend,bucket);
        context.write(key, new Text(result));
    }
}
