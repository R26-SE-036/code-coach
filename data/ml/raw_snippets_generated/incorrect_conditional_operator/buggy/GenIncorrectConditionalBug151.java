public class GenIncorrectConditionalBug151 {
    static String report(boolean open) {
        if (open = true) {
            return "shipped";
        }
        return "new";
    }

    static String describe1(int total) {
        if (total < 5) {
            return "low";
        } else if (total > 20) {
            return "high";
        }
        return "medium";
    }
}
