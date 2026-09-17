package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug018 {
    static double discountFor(String tier) {
        double discount = 0;
        switch (tier) {
            case "gold":
                discount = 0.20;
            case "silver":
                discount = 0.10;
                break;
            case "bronze":
                discount = 0.05;
                break;
            default:
                discount = 0;
        }
        return discount;
    }
}
