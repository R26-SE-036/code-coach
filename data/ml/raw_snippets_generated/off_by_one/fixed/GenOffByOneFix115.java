public class GenOffByOneFix115 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void show(int[] marks) {
        for (int i = 0; i < marks.length; i++) {
            System.out.println(marks[i]);
        }
    }
}
