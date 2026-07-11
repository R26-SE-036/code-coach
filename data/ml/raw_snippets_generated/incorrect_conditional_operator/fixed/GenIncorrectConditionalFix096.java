public class GenIncorrectConditionalFix096 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static boolean matches(boolean running, boolean armed) {
        if (running == armed) {
            return true;
        }
        return false;
    }

    static void printAll2(int[] ages) {
        for (int value : ages) {
            System.out.println(value);
        }
    }
}
