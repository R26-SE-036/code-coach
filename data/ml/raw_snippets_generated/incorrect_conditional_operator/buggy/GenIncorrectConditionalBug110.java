public class GenIncorrectConditionalBug110 {
    static String report(boolean loaded) {
        if (loaded = true) {
            return "archived";
        }
        return "shipped";
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
