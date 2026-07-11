public class GenCleanVerboseBoolean024 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void printAll2(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static String toggle(boolean verified) {
        if (verified == true) {
            return "on";
        }
        return "off";
    }

    static void printAll3(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }
}
