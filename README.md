# vernpanter.com

How to manage [vernpanter.com](https://vernpanter.com). This page is not part of
the website.

Everything happens on github.com, so there is nothing to install. Sign in first.
Changes are live a few minutes after you press the green **Commit changes**
button.

## Placeholders

The site starts out full of placeholders. The placeholder pictures hide on their
own once you add a real work to that section (2D and 3D are separate). Replace
the placeholder words using the links under
[Change the words](#change-the-words).

## Add a 2D work

1. Open the [2D upload page](https://github.com/vernpanter/vernpanter.github.io/upload/main/art/2d).
2. Drag in 1 or more pictures and press **Commit changes**.

The file name becomes the title, so `blue-door.jpg` shows up as "Blue door".
Pictures can be up to 25 MB each.

## Add a 3D work

1. Put all the photos of the work in a folder named after it, like `tall-bird`.
2. Open the [3D upload page](https://github.com/vernpanter/vernpanter.github.io/upload/main/art/3d).
3. Drag in the folder and press **Commit changes**.

The photos show in file name order, so start the names with 1, 2, 3. A work
with only 1 photo does not need a folder.

## Add details or change the order

Edit the [2D details](https://github.com/vernpanter/vernpanter.github.io/edit/main/_data/works_2d.yml)
or the [3D details](https://github.com/vernpanter/vernpanter.github.io/edit/main/_data/works_3d.yml).
Each file has an example to copy. Works in the list come first, in that order,
and the rest follow by file name.

## Change the words

- [Name, email, links and home page picture](https://github.com/vernpanter/vernpanter.github.io/edit/main/_data/artist.yml)
- [About page](https://github.com/vernpanter/vernpanter.github.io/edit/main/about.md)
- [CV page](https://github.com/vernpanter/vernpanter.github.io/edit/main/cv.md)
- [Contact page](https://github.com/vernpanter/vernpanter.github.io/edit/main/contact.md)

On the About, CV and Contact pages, leave the block between the `---` lines
alone and type below it.

## Remove a work

Open the picture in [art](https://github.com/vernpanter/vernpanter.github.io/tree/main/art),
press the **...** menu and pick **Delete file**. For a 3D work, open its folder
and pick **Delete directory** from the same menu. Delete its entry from the
details file too.

## When something goes wrong

GitHub sends an email when a file has a mistake in it. With picture resizing
turned on (below) the site stays the way it was until the mistake is fixed. Open
the [Actions page](https://github.com/vernpanter/vernpanter.github.io/actions),
click the run with the red X, and look for the lines that say PROBLEM.

## Private information

**Anyone can download the original pictures from this repository.** Phone
photos can hold the location where they were taken, so turn location off or
remove it before you upload. Deleting a picture later does not remove it from
the history.

## Turn on picture resizing (once)

Until this is done the site sends visitors the full size pictures and cannot
show iPhone HEIC photos. Only the `vernpanter` account can change it.

1. Open [Settings, Pages](https://github.com/vernpanter/vernpanter.github.io/settings/pages).
2. Under **Source**, pick **GitHub Actions**.
3. Open [the Site workflow](https://github.com/vernpanter/vernpanter.github.io/actions/workflows/site.yml)
   and press **Run workflow**.
