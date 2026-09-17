package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix026 {
    static int priceOf(int slot) {
        int price;
        switch (slot) {
            case 1:
                price = 120;
                break;
            case 2:
                price = 150;
                break;
            case 3:
                price = 90;
                break;
            case 4:
                price = 200;
                break;
            default:
                price = -1;
        }
        return price;
    }
}
