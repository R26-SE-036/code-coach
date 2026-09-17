package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug015 {
    static void printItem(int code) {
        switch (code) {
            case 10:
                System.out.println("Bread  2.50");
                break;
            case 20:
                System.out.println("Milk   1.20");
            case 30:
                System.out.println("Eggs   3.10");
                break;
            default:
                System.out.println("Unknown item");
        }
    }
}
