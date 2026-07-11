public class GenIncorrectConditionalBug055 {
    static void announce(int level) {
        if (level = 10) {
            System.out.println("hit the target");
        }
    }

    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
