package com.trendpulse;
import org.apache.hadoop.io.*; import org.apache.hadoop.mapreduce.Mapper; import java.io.IOException; import java.util.*;
/** Engagement Analysis Mapper. Buckets: Low/Medium/High/Very_High. Key=bucket, Value=views|likes|comments|trending */
public class EngagementMapper extends Mapper<LongWritable,Text,Text,Text> {
    private boolean isHeader=true;
    private static final int IDX_ENG=17,IDX_VIEWS=8,IDX_LIKES=9,IDX_COMMENTS=11,IDX_TREND=27;
    @Override public void map(LongWritable key, Text value, Context ctx) throws IOException,InterruptedException {
        String line=value.toString().trim();
        if(isHeader&&line.startsWith("video_id")){isHeader=false;return;} isHeader=false;
        if(line.isEmpty())return;
        String[] c=csv(line); if(c.length<28)return;
        try{
            double eng=pD(c,IDX_ENG); long v=pL(c,IDX_VIEWS),lk=pL(c,IDX_LIKES),cm=pL(c,IDX_COMMENTS); int td=pI(c,IDX_TREND,1);
            String bucket=eng<0.01?"Low":eng<0.05?"Medium":eng<0.15?"High":"Very_High";
            ctx.write(new Text(bucket),new Text(v+"|"+lk+"|"+cm+"|"+td));
        }catch(Exception e){ctx.getCounter("TrendPulse","Errors").increment(1);}
    }
    private String get(String[] c,int i,String d){return i<c.length?c[i].trim().replace("\"",""):d;}
    private long pL(String[] c,int i){try{return Math.max(0,Long.parseLong(get(c,i,"0")));}catch(Exception e){return 0;}}
    private double pD(String[] c,int i){try{return Double.parseDouble(get(c,i,"0"));}catch(Exception e){return 0.0;}}
    private int pI(String[] c,int i,int d){try{return Math.max(1,Integer.parseInt(get(c,i,String.valueOf(d))));}catch(Exception e){return d;}}
    private String[] csv(String line){List<String> f=new ArrayList<>();StringBuilder sb=new StringBuilder();boolean q=false;
        for(char ch:line.toCharArray()){if(ch=='"'){q=!q;}else if(ch==','&&!q){f.add(sb.toString());sb=new StringBuilder();}else{sb.append(ch);}}
        f.add(sb.toString());return f.toArray(new String[0]);}
}
