public class GenCleanTailIndex001 {
    static int tail(int[] sizes) {
        return sizes[sizes.length - 1];
    }

    static int sum1(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }
}
