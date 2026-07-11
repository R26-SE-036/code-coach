public class GenCleanVerboseBoolean011 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String toggle(boolean verified) {
        if (verified == true) {
            return "on";
        }
        return "off";
    }
}
