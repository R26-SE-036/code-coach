public class GenIncorrectConditionalBug099 {
    static boolean isEven1(int budget) {
        return budget % 2 == 0;
    }

    static void announce(int limit) {
        if (limit = 10) {
            System.out.println("hit the target");
        }
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String describe3(int count) {
        if (count < 5) {
            return "low";
        } else if (count > 20) {
            return "high";
        }
        return "medium";
    }

    static void printAll4(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }

    static void printAll5(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }
}
