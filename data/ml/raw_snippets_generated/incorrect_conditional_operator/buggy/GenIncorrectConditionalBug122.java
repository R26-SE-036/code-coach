public class GenIncorrectConditionalBug122 {
    static String describe1(int total) {
        if (total < 5) {
            return "low";
        } else if (total > 20) {
            return "high";
        }
        return "medium";
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void printAll4(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int sum6(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static boolean matches(boolean running, boolean open) {
        if (running = open) {
            return true;
        }
        return false;
    }
}
