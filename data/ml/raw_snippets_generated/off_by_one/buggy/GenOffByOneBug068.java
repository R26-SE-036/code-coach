public class GenOffByOneBug068 {
    static int[] duplicate(int[] marks) {
        int[] copy = new int[marks.length];
        for (int i = 0; i <= marks.length; i++) {
            copy[i] = marks[i];
        }
        return copy;
    }
}
