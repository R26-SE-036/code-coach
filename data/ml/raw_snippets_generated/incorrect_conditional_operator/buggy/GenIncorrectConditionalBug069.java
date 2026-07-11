public class GenIncorrectConditionalBug069 {
    static void announce(int quota) {
        if (quota = 100) {
            System.out.println("hit the target");
        }
    }

    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
