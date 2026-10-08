package com.trendpulse;
import org.apache.hadoop.io.*;
import org.apache.hadoop.mapreduce.Mapper;
import java.io.IOException;
import java.util.*;

/** TrendPulse - Upload Time Analysis Mapper. Key=publish_hour, Value=views|engagement_rate|trending_duration */
public class UploadTimeMapper extends Mapper<LongWritable, Text, Text, Text> {
    private boolean isHeader = true;
    private static final int IDX_PUBLISH_HOUR = 14;
    private static final int IDX_VIEWS = 8;
    private static final int IDX_ENGAGEMENT = 17;
    private static final int IDX_TRENDING = 27;
    private static final int IDX_BUCKET = 19;

    @Override
    public void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
        String line = value.toString().trim();
        if (isHeader && line.startsWith("video_id")) { isHeader = false; return; }
        isHeader = false;
        if (line.isEmpty()) return;
        String[] cols = parseCsv(line);
        if (cols.length < 20) return;
        try {
            String hour = getField(cols, IDX_PUBLISH_HOUR, "0");
            if (hour.isEmpty() || hour.equals("0")) return;
            long views = parseLong(cols, IDX_VIEWS);
            double eng = parseDouble(cols, IDX_ENGAGEMENT);
            int trend = parseInt(cols, IDX_TRENDING, 1);
            String bucket = getField(cols, IDX_BUCKET, "Unknown");
            context.write(new Text(hour), new Text(views + "|" + eng + "|" + trend + "|" + bucket));
        } catch (Exception e) { context.getCounter("TrendPulse","MalformedRecords").increment(1); }
    }
    private String getField(String[] cols, int idx, String def) {
        return (idx < cols.length) ? cols[idx].trim().replace("\"","") : def;
    }
    private long parseLong(String[] cols, int idx) {
        try { return Math.max(0, Long.parseLong(getField(cols,idx,"0"))); } catch(Exception e){return 0;}
    }
    private double parseDouble(String[] cols, int idx) {
        try { return Double.parseDouble(getField(cols,idx,"0")); } catch(Exception e){return 0.0;}
    }
    private int parseInt(String[] cols, int idx, int def) {
        try { return Math.max(1, Integer.parseInt(getField(cols,idx,String.valueOf(def)))); } catch(Exception e){return def;}
    }
    private String[] parseCsv(String line) {
        List<String> f = new ArrayList<>(); StringBuilder sb = new StringBuilder(); boolean q=false;
        for(char c:line.toCharArray()){if(c=='"'){q=!q;}else if(c==','&&!q){f.add(sb.toString());sb=new StringBuilder();}else{sb.append(c);}}
        f.add(sb.toString()); return f.toArray(new String[0]);
    }
}
