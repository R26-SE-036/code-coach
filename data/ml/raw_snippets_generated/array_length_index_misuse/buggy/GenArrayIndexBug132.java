public class GenArrayIndexBug132 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void showLast(int[] ages) {
        System.out.println(ages[ages.length]);
    }
}
