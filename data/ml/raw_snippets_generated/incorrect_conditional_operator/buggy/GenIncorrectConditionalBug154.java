public class GenIncorrectConditionalBug154 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void printAll2(int[] ages) {
        for (int value : ages) {
            System.out.println(value);
        }
    }

    static String report(boolean armed) {
        if (armed = true) {
            return "active";
        }
        return "new";
    }

    static void printAll3(int[] ages) {
        for (int value : ages) {
            System.out.println(value);
        }
    }
}
