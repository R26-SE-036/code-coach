public class GenArrayIndexFix008 {
    static void showLast(int[] marks) {
        System.out.println(marks[marks.length - 1]);
    }

    static int largest1(int[] marks) {
        int best = marks[0];
        for (int i = 1; i < marks.length; i++) {
            if (marks[i] > best) {
                best = marks[i];
            }
        }
        return best;
    }

    static int drain2(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }
}
