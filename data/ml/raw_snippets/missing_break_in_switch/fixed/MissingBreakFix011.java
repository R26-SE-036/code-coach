package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix011 {
    public static void main(String[] args) {
        int[] readings = { 1, 3, 2, 3 };
        int cold = 0;
        int mild = 0;
        int hot = 0;
        for (int reading : readings) {
            switch (reading) {
                case 1:
                    cold++;
                    break;
                case 2:
                    mild++;
                    break;
                case 3:
                    hot++;
                    break;
            }
        }
        System.out.println(cold + " " + mild + " " + hot);
    }
}
