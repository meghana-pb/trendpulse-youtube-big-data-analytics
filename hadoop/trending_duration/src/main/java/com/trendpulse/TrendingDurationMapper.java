package com.trendpulse;
import org.apache.hadoop.io.*; import org.apache.hadoop.mapreduce.Mapper; import java.io.IOException; import java.util.*;
/** Trending Duration Analysis Mapper. Buckets: 1_day/2-3_days/4-7_days/8-14_days/15+_days */
public class TrendingDurationMapper extends Mapper<LongWritable,Text,Text,Text> {
    private boolean isHeader=true;
    private static final int IDX_TREND=27,IDX_VIEWS=8,IDX_ENG=17,IDX_TITLE_LEN=13,IDX_CAT=3;
    @Override public void map(LongWritable key, Text value, Context ctx) throws IOException,InterruptedException {
        String line=value.toString().trim();
        if(isHeader&&line.startsWith("video_id")){isHeader=false;return;} isHeader=false;
        if(line.isEmpty())return;
        String[] c=csv(line); if(c.length<28)return;
        try{
            int td=pI(c,IDX_TREND,1); long v=pL(c,IDX_VIEWS); double eng=pD(c,IDX_ENG); int tl=pI(c,IDX_TITLE_LEN,0); String cat=get(c,IDX_CAT,"0");
            String bucket=td==1?"1_day":td<=3?"2-3_days":td<=7?"4-7_days":td<=14?"8-14_days":"15+_days";
            ctx.write(new Text(bucket),new Text(v+"|"+eng+"|"+tl+"|"+cat));
        }catch(Exception e){ctx.getCounter("TrendPulse","Errors").increment(1);}
    }
    private String get(String[] c,int i,String d){return i<c.length?c[i].trim().replace("\"",""):d;}
    private long pL(String[] c,int i){try{return Math.max(0,Long.parseLong(get(c,i,"0")));}catch(Exception e){return 0;}}
    private double pD(String[] c,int i){try{return Double.parseDouble(get(c,i,"0"));}catch(Exception e){return 0.0;}}
    private int pI(String[] c,int i,int d){try{return Math.max(0,Integer.parseInt(get(c,i,String.valueOf(d))));}catch(Exception e){return d;}}
    private String[] csv(String line){List<String> f=new ArrayList<>();StringBuilder sb=new StringBuilder();boolean q=false;
        for(char ch:line.toCharArray()){if(ch=='"'){q=!q;}else if(ch==','&&!q){f.add(sb.toString());sb=new StringBuilder();}else{sb.append(ch);}}
        f.add(sb.toString());return f.toArray(new String[0]);}
}
