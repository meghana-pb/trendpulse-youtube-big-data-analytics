package com.trendpulse;
import org.apache.hadoop.conf.Configuration; import org.apache.hadoop.fs.Path; import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job; import org.apache.hadoop.mapreduce.lib.input.FileInputFormat; import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
public class TrendingDurationDriver {
    public static void main(String[] args) throws Exception {
        if(args.length<2){System.err.println("Usage: TrendingDurationDriver <in> <out>");System.exit(1);}
        Configuration conf=new Configuration(); Job job=Job.getInstance(conf,"TrendPulse-TrendingDurationAnalysis");
        job.setJarByClass(TrendingDurationDriver.class); job.setMapperClass(TrendingDurationMapper.class);
        job.setReducerClass(TrendingDurationReducer.class); job.setOutputKeyClass(Text.class); job.setOutputValueClass(Text.class);
        job.setNumReduceTasks(1);
        FileInputFormat.addInputPath(job,new Path(args[0])); FileOutputFormat.setOutputPath(job,new Path(args[1]));
        System.exit(job.waitForCompletion(true)?0:1);
    }
}
