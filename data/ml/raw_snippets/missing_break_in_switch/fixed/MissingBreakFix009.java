package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix009 {
    public static void main(String[] args) {
        int level = 2;
        int bonus = 0;
        switch (level) {
            case 3:
                bonus = 300;
                break;
            case 2:
                bonus = 200;
                break;
            case 1:
                bonus = 100;
                break;
            default:
                bonus = 0;
        }
        System.out.println("Bonus: " + bonus);
    }
}
