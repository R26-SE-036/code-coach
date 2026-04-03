package data.ml.raw_snippets.off_by_one.fixed;

public class OffByOneFix006 {
    public static void main(String[] args) {
        int[] marks = { 65, 70, 80, 90 };
        int highest = 0;

        for (int i = 0; i < marks.length; i++) {
            if (marks[i] > highest) {
                highest = marks[i];
            }
        }

        System.out.println(highest);
    }
}