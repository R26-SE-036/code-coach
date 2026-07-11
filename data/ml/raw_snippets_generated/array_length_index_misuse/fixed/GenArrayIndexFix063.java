public class GenArrayIndexFix063 {
    static String describe1(int count) {
        if (count < 100) {
            return "low";
        } else if (count > 500) {
            return "high";
        }
        return "medium";
    }

    static String describe2(int quota) {
        if (quota < 10) {
            return "low";
        } else if (quota > 50) {
            return "high";
        }
        return "medium";
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int lastOf(int[] weights) {
        return weights[weights.length - 1];
    }
}
