public class GenArrayIndexBug094 {
    static boolean isEven1(int budget) {
        return budget % 2 == 0;
    }

    static int lastOf(int[] marks) {
        return marks[marks.length];
    }
}
