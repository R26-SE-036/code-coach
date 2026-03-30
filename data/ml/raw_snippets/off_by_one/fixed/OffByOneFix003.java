package data.ml.raw_snippets.off_by_one.fixed;

public class OffByOneFix003 {
    public static void main(String[] args) {
        int[] values = { 5, 6, 7 };
        int sum = 0;

        for (int i = 0; i < values.length; i++) {
            sum += values[i];
        }

        System.out.println(sum);
    }
}