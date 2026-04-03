public class ArrayIndexFix027 {
    public int chooseEnd(int[] queue) {
        int selected = queue[queue.length - 1];
        if (selected > 5) {
            return selected;
        }
        return 0;
    }
}