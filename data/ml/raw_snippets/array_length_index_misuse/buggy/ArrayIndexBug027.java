public class ArrayIndexBug027 {
    public int chooseEnd(int[] queue) {
        int selected = queue[queue.length];
        if (selected > 5) {
            return selected;
        }
        return 0;
    }
}