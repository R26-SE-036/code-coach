public class GenIncorrectConditionalBug012 {
    static String describe1(int level) {
        if (level < 100) {
            return "low";
        } else if (level > 500) {
            return "high";
        }
        return "medium";
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static boolean matches(boolean running, boolean active) {
        if (running = active) {
            return true;
        }
        return false;
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int largest4(int[] ratings) {
        int best = ratings[0];
        for (int i = 1; i < ratings.length; i++) {
            if (ratings[i] > best) {
                best = ratings[i];
            }
        }
        return best;
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
