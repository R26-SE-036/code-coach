public class GenIncorrectConditionalBug029 {
    static String describe1(int budget) {
        if (budget < 5) {
            return "low";
        } else if (budget > 20) {
            return "high";
        }
        return "medium";
    }

    static String report(boolean active) {
        if (active = true) {
            return "queued";
        }
        return "expired";
    }

    static boolean isEven2(int steps) {
        return steps % 2 == 0;
    }
}
