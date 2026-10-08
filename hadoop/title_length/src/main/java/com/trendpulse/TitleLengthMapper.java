package com.trendpulse;
import org.apache.hadoop.io.*; import org.apache.hadoop.mapreduce.Mapper;
import java.io.IOException; import java.util.*;
/** Title Length Analysis Mapper. Key=title_length_bucket, Value=views|engagement|trending */
public class TitleLengthMapper extends Mapper<LongWritable,Text,Text,Text> {
    private boolean isHeader=true;
    private static final int IDX_BUCKET=22, IDX_VIEWS=8, IDX_ENG=17, IDX_TREND=27;
    @Override public void map(LongWritable key, Text value, Context ctx) throws IOException,InterruptedException {
        String line=value.toString().trim();
        if(isHeader&&line.startsWith("video_id")){isHeader=false;return;} isHeader=false;
        if(line.isEmpty()) return;
        String[] c=csv(line); if(c.length<25) return;
        try{
            String bucket=get(c,IDX_BUCKET,"Unknown"); if(bucket.isEmpty()) return;
            long v=pL(c,IDX_VIEWS); double e=pD(c,IDX_ENG); int t=pI(c,IDX_TREND,1);
            ctx.write(new Text(bucket), new Text(v+"|"+e+"|"+t));
        }catch(Exception ex){ctx.getCounter("TrendPulse","Errors").increment(1);}
    }
    private String get(String[] c,int i,String d){return i<c.length?c[i].trim().replace("\"",""):d;}
    private long pL(String[] c,int i){try{return Math.max(0,Long.parseLong(get(c,i,"0")));}catch(Exception e){return 0;}}
    private double pD(String[] c,int i){try{return Double.parseDouble(get(c,i,"0"));}catch(Exception e){return 0.0;}}
    private int pI(String[] c,int i,int d){try{return Math.max(1,Integer.parseInt(get(c,i,String.valueOf(d))));}catch(Exception e){return d;}}
    private String[] csv(String line){List<String> f=new ArrayList<>();StringBuilder sb=new StringBuilder();boolean q=false;
        for(char ch:line.toCharArray()){if(ch=='"'){q=!q;}else if(ch==','&&!q){f.add(sb.toString());sb=new StringBuilder();}else{sb.append(ch);}}
        f.add(sb.toString());return f.toArray(new String[0]);}
}
