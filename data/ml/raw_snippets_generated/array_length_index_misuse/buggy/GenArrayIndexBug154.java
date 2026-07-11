public class GenArrayIndexBug154 {
    static int sum1(int[] totals) {
        int total = 0;
        for (int i = 0; i < totals.length; i++) {
            total += totals[i];
        }
        return total;
    }

    static void showLast(int[] marks) {
        System.out.println(marks[marks.length]);
    }
}
