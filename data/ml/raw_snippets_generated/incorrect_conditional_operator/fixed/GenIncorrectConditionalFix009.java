public class GenIncorrectConditionalFix009 {
    static boolean matches(boolean open, boolean done) {
        if (open == done) {
            return true;
        }
        return false;
    }

    static String describe1(int attempts) {
        if (attempts < 100) {
            return "low";
        } else if (attempts > 500) {
            return "high";
        }
        return "medium";
    }

    static boolean isEven2(int count) {
        return count % 2 == 0;
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int average4(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
